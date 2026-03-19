function getClassNames(content) {
  if (!!content) {
    return content
      .replace(/\n/g, '')
      .replace(/\r/g, '')
      .replace(/\s/g, '')
      .split(';')
      .map((v) => (v || '').split('|')?.[0])
      .filter((v) => v !== undefined && v !== null && v !== '')
      .map((v) => ({ label: v }))
  } else {
    return []
  }
}

function generateDesctiptionItem(label, value, colon = false) {
  let _label = label
  if (typeof label === 'string' && label) {
    if ((label.startsWith('<strong') && label.endsWith('</strong>')) || label.endsWith('：')) {
      _label = label
    } else {
      _label = `${label}${colon ? '：' : ''}`
    }
  }
  return `
                      <p class="block-class">
                        <strong class="label-class">
                          ${_label}
                        </strong>
                        <span class="dots-class"></span>
                        <span class="content-class">${value}</span>
                      </p>
                    `
}

function generateSubDesctiptionItem(label, value, colon = false) {
  return generateDesctiptionItem(`<strong class="sub-label-class">${label}${colon ? '：' : ''}</strong>`, value)
}

function render(container, tagName, properties, children) {
  if (!tagName) {
    return
  }
  const ele = document.createElement(tagName)
  if ((properties && typeof properties === 'string') || typeof properties === 'number') {
    ele.textContent = properties
  } else if (properties && typeof properties === 'object') {
    Object.entries(properties).forEach(([key, value]) => {
      if (key) {
        ele[key] = value
      }
    })
  }

  if (children && typeof children === 'object' && children instanceof Array && children.length) {
    children.forEach((child) => {
      if (ele) {
        ele.appendChild(child)
      }
    })
  }

  if (container) {
    container.appendChild(ele)
  }

  return ele
}
